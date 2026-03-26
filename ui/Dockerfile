# Stage 1: Build Angular App
FROM node:20 as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build --configuration=production

# Stage 2: Serve with Nginx
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist/automated-call-dashboard/browser /usr/share/nginx/html
EXPOSE 8501
CMD ["nginx", "-g", "daemon off;"]
