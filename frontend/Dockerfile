FROM node:20-alpine AS base

FROM base AS deps
WORKDIR /app
COPY package.json ./
RUN npm ci --only=production

FROM base AS development
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
CMD ["npm", "run", "dev"]

FROM base AS production
WORKDIR /app
COPY package.json ./
RUN npm ci
COPY . .
RUN npm run build
CMD ["npm", "start"]
