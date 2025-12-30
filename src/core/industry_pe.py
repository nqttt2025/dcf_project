"""
Industry PE Module - Lấy PE của ngành từ vnstock và đề xuất Base PE
Tích hợp logic từ scripts/analysis/calculate_pe.py
"""
import sys
from io import StringIO

try:
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = StringIO()
    sys.stderr = StringIO()
    try:
        from vnstock import Vnstock
        HAS_VNSTOCK = True
    except ImportError:
        HAS_VNSTOCK = False
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
except:
    HAS_VNSTOCK = False
    sys.stdout = old_stdout
    sys.stderr = old_stderr

from ..utils.cache_manager import get_cache_manager
from ..utils.logger import get_logger
from .fcfs import price_board_stock, get_earnings_per_share_Diluted

logger = get_logger()
cache_manager = get_cache_manager()

# Bảng đề xuất Base PE theo ngành (từ calculate_pe.py)
INDUSTRY_BASE_PE = {
    'banking': (7.0, 8.0),
    'real_estate': (8.0, 9.0),
    'technology': (9.0, 10.0),
    'consumer': (8.5, 9.0),
    'energy': (7.5, 8.5),
    'industrial': (8.0, 9.0),
    'aviation': (8.5, 9.5),
}

# Mapping từ tên ngành tiếng Việt sang key
INDUSTRY_MAPPING = {
    'ngân hàng': 'banking',
    'bất động sản': 'real_estate',
    'công nghệ': 'technology',
    'tiêu dùng': 'consumer',
    'năng lượng': 'energy',
    'công nghiệp': 'industrial',
    'hàng không': 'aviation',
}


def get_industry_pe(ticker):
    """
    Lấy PE trung bình của ngành từ vnstock
    
    Args:
        ticker: Mã cổ phiếu
        
    Returns:
        PE trung bình của ngành (float) hoặc None nếu không lấy được
    """
    ticker = ticker.upper()
    
    if not HAS_VNSTOCK:
        logger.warning("vnstock not installed. Cannot get industry PE.")
        return None
    
    try:
        logger.info(f"Fetching industry PE for {ticker} using vnstock...")
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        try:
            sys.stdout = StringIO()
            sys.stderr = StringIO()
            stock = Vnstock().stock(symbol=ticker.upper(), source="VCI")
            
            # Thử lấy từ industry comparison
            industry_df = stock.company.industry_comparison()
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
        
        if industry_df is not None and not industry_df.empty:
            # Tìm cột PE trong industry comparison
            pe_column = None
            for col in industry_df.columns:
                if 'pe' in col.lower() or 'p/e' in col.lower():
                    pe_column = col
                    break
            
            if pe_column:
                # Lấy PE của các công ty trong cùng ngành (bỏ qua công ty hiện tại)
                pe_values = []
                for idx, row in industry_df.iterrows():
                    pe_val = row[pe_column]
                    # Bỏ qua giá trị None, NaN, hoặc công ty hiện tại
                    if pe_val is not None and str(pe_val).lower() != 'nan':
                        try:
                            pe_float = float(pe_val)
                            if pe_float > 0 and pe_float < 1000:  # Filter outliers
                                pe_values.append(pe_float)
                        except (ValueError, TypeError):
                            continue
                
                if len(pe_values) > 0:
                    # Tính trung bình PE của ngành
                    industry_pe = sum(pe_values) / len(pe_values)
                    logger.info(f"Industry PE for {ticker}: {industry_pe:.2f} (from {len(pe_values)} companies)")
                    cache_manager.set_with_timestamp(ticker, "industry_pe", industry_pe)
                    return industry_pe
                else:
                    logger.warning(f"No valid PE values found in industry comparison for {ticker}")
            else:
                logger.warning(f"PE column not found in industry comparison for {ticker}")
        else:
            logger.warning(f"No industry comparison data available for {ticker}")
        
        # Fallback: Thử lấy từ ratio summary nếu có industry average
        try:
            ratio_df = stock.company.ratio_summary()
            if ratio_df is not None and not ratio_df.empty:
                # Tìm cột industry PE hoặc sector PE
                for col in ratio_df.columns:
                    if 'industry' in col.lower() and 'pe' in col.lower():
                        industry_pe = float(ratio_df[col].iloc[0])
                        if industry_pe > 0:
                            logger.info(f"Industry PE for {ticker} from ratio summary: {industry_pe:.2f}")
                            cache_manager.set_with_timestamp(ticker, "industry_pe", industry_pe)
                            return industry_pe
        except Exception as e:
            logger.debug(f"Could not get industry PE from ratio summary: {e}")
        
        return None
        
    except Exception as e:
        logger.debug(f"Error fetching industry PE for {ticker}: {e}")
        # Check cache as fallback
        if cache_manager.exists(ticker, "industry_pe"):
            industry_pe = cache_manager.get_with_timestamp(ticker, "industry_pe")
            logger.info(f"Using cached industry PE for {ticker}: {industry_pe}")
            return industry_pe
        return None


def get_current_pe(ticker):
    """
    Tính PE hiện tại của mã cổ phiếu
    
    Args:
        ticker: Mã cổ phiếu
        
    Returns:
        float: PE ratio, hoặc None nếu không tính được
    """
    try:
        price = price_board_stock(ticker.upper())
        eps = get_earnings_per_share_Diluted(ticker.upper())
        
        if eps and eps > 0:
            pe = price / eps
            logger.info(f"{ticker}: Price={price:,.0f}, EPS={eps:,.2f}, PE={pe:.2f}")
            return pe
        else:
            logger.warning(f"{ticker}: EPS <= 0, không thể tính PE")
            return None
    except Exception as e:
        logger.debug(f"Error calculating current PE for {ticker}: {e}")
        return None


def get_industry_from_vnstock(ticker):
    """
    Lấy thông tin ngành từ vnstock
    
    Args:
        ticker: Mã cổ phiếu
        
    Returns:
        str: Tên ngành (industry key) hoặc None
    """
    if not HAS_VNSTOCK:
        return None
    
    try:
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        try:
            sys.stdout = StringIO()
            sys.stderr = StringIO()
            stock = Vnstock().stock(symbol=ticker.upper(), source="VCI")
            info = stock.company.info()
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
        
        if isinstance(info, dict):
            # Thử các key có thể có
            industry = info.get('industry') or info.get('sector') or info.get('ngành')
            if industry:
                # Chuyển đổi sang key chuẩn
                industry_lower = str(industry).lower()
                for vi_name, key in INDUSTRY_MAPPING.items():
                    if vi_name in industry_lower:
                        return key
                # Thử match trực tiếp
                if industry_lower in INDUSTRY_BASE_PE:
                    return industry_lower
        return None
    except Exception as e:
        logger.debug(f"Could not get industry from vnstock for {ticker}: {e}")
        return None


def suggest_base_pe(ticker, industry=None, current_pe=None):
    """
    Đề xuất Base PE dựa trên ngành và PE hiện tại
    Tích hợp logic từ calculate_pe.py
    
    Args:
        ticker: Mã cổ phiếu
        industry: Ngành nghề (banking, real_estate, technology, consumer, energy, industrial, aviation)
                 Nếu None, sẽ tự động lấy từ vnstock
        current_pe: PE hiện tại (nếu None sẽ tự tính)
    
    Returns:
        float: Base PE đề xuất
    """
    # Tính PE hiện tại nếu chưa có
    if current_pe is None:
        current_pe = get_current_pe(ticker)
    
    # Lấy ngành từ vnstock nếu chưa có
    if industry is None:
        industry = get_industry_from_vnstock(ticker)
    
    # Nếu có thông tin ngành
    if industry and industry.lower() in INDUSTRY_BASE_PE:
        base_pe_min, base_pe_max = INDUSTRY_BASE_PE[industry.lower()]
        
        # Nếu PE hiện tại quá cao (>30), dùng giá trị thấp hơn
        if current_pe and current_pe > 30:
            suggested = base_pe_min
        else:
            suggested = (base_pe_min + base_pe_max) / 2
        
        logger.info(f"{ticker} ({industry}): Đề xuất Base PE = {suggested:.2f}")
        return suggested
    
    # Mặc định
    logger.info(f"{ticker}: Sử dụng Base PE mặc định = 8.5")
    return 8.5


def get_pe_analysis(ticker):
    """
    Lấy phân tích PE đầy đủ cho một mã cổ phiếu
    
    Args:
        ticker: Mã cổ phiếu
        
    Returns:
        dict: {
            'current_pe': float,
            'industry_pe': float,
            'suggested_base_pe': float,
            'industry': str
        }
    """
    current_pe = get_current_pe(ticker)
    industry_pe = get_industry_pe(ticker)
    industry = get_industry_from_vnstock(ticker)
    suggested_base_pe = suggest_base_pe(ticker, industry, current_pe)
    
    return {
        'current_pe': current_pe,
        'industry_pe': industry_pe,
        'suggested_base_pe': suggested_base_pe,
        'industry': industry
    }

