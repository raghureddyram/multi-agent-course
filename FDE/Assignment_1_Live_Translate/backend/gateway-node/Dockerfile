FROM node:20-alpine

WORKDIR /app

# install deps first for layer caching (use lockfile for reproducible builds)
COPY package.json package-lock.json* ./
RUN npm ci --omit=dev || npm install --omit=dev

COPY . .

ENV PORT=8080
EXPOSE 8080

CMD ["node", "server.js"]
