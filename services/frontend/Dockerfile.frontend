FROM nginx:alpine

# Build argument for version
ARG VERSION=latest
ENV APP_VERSION=${VERSION}

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx config
COPY services/frontend/nginx.conf /etc/nginx/conf.d/

# Copy static files
COPY services/frontend/static /usr/share/nginx/html/static
COPY services/frontend/index.html /usr/share/nginx/html/

LABEL version="${VERSION}"
LABEL maintainer="DCF Project"

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

