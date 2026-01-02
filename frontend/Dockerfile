# Frontend Dockerfile para React + Vite
FROM node:20-alpine AS builder

# Directorio de trabajo
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci

# Copiar código fuente
COPY . .

RUN npm run build

# Producción con nginx
FROM nginx:alpine

# Copiar archivos compilados
COPY --from=builder /app/dist /usr/share/nginx/html

# Copiar configuración de nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
