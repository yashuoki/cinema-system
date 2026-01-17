FROM nginx:alpine

# Копируем конфиг nginx
COPY nginx.conf /etc/nginx/nginx.conf

# Копируем статические файлы
COPY public /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
