#!/usr/bin/python3
# Copyright © NQT
# tiennguyen047@gmail.com

from vnstock import *
import pandas as pd
import requests


class Company():
    """this class have include balance sheet's metadata of company by year
    """

    year = 0
    """hoạt động tài chính theo năm của doanh nghiệp
    """

    net_revenue = 0 #doanh thu thuan
    percent_net_revenue = 0 #phan tram doanh thu thuan
    """doanh thu thuần là khoản tiền doanh nghiệp nhận về từ việc bán hàng hóa và dịch vụ được khấu trừ
        các loại thuế và các khoản giảm trừ
        (bao gồm thuế xuất nhập khẩu, doanh thu bị trả lại, giảm giá bán hàng, chiết khấu thương mại)
    """

    selling_expenses = 0 #Chi phí bán hàng
    percent_selling_expenses = 0 #tỉ trọng chi phi ban hang
    """chi phí bán hàng là toàn bộ chi phí phát sinh liên quan đến quá trình bán sản phẩm, hàng hóa và cung
        cấp dịch vụ
    """

    financial_charges = 0
    """chi phí tài chính(Financial Charges) là một khoản chi hoặc khoản thiệt hại(lỗ) phát sinh từ hoạt động
        tài chính của doanh nghiệp. Hoạt động tài chính có thể hiểu như hoạt động đầu đầu tư chứng khoán, cho vay
        góp vốn, etc
    """

    Ebit = 0 # lợi nhuận trước thuế
    """Ebit (Earnings Before Interest and Taxs) được hiểu là lợi nhuận trước thuế và lãi vay của doanh nghiệp.
        đây là một khoản lợi nhuận mà mọt công ty thu đc từ việc kinh doanh, chưa trừ đi các khoản trả lãi vay và
        thuế thu nhập doanh nghiệp. Ebit được sử dụng để đánh giá khả năng sinh lời của doanh nghiệp
    """

    profit_financial = 0
    """profit from financial activities
    """

    profit_other = 0
    """lợi nhuận từ hoạt động khác ví dụ như tài chính, đầu tư, include profit from financial activities
    """

    CIT = 0
    """ Corporate income tax, thuế doanh nghiệp là một loại thế mà nhà nước trực tiếp thu vào ngân sách của nhà nước,
        tính trên thu nhập chịu thuế của doanh nghiệp
    """

    gross_profit = 0
    gross_profit_margin = 0 #biên lợi nhuận gộp GPM
    """lợi nhuận gộp (gross profit) là lợi nhuận sau khi trừ đi các chi phí
        liên quan đến quá trình sản suất và bán sản phẩm/dịch vụ từ nguồn doanh thu của doanh nghiệp
        Biên lợi nhuận gộp (tiếng anh là Gross Profit Margin) là một chỉ tiêu đánh giá khả năng sinh lời
        của doanh nghiệp. Chỉ tiêu này được tính theo tỷ lệ phần trăm và cho biết với mỗi đồng doanh thu
        tạo ra thì doanh nghiệp thu về được bao nhiêu đồng lợi nhuận gộp.
    """

    def __init__(self, stock_item):
        self.stock_item = stock_item


    def test():
        pass


    def import_data(path):
        """for import data from

        Args:
            path (string): path of xlsx file balance sheet by year
        """
        pass




if __name__ == "__main__":
    pass