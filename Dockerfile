FROM nginx:alpine

WORKDIR /usr/share/nginx/html

COPY static-website-example/ .

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
