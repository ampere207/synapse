# Frontend Dockerfile - Multi-stage build for Next.js
FROM node:20-alpine AS builder

WORKDIR /app

# Set build arguments for environment variables
ARG NEXT_PUBLIC_API_URL=http://localhost:8000/api
ARG NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Set environment variables for build
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_WS_URL=$NEXT_PUBLIC_WS_URL

# Install dependencies (including dev)
COPY package.json package-lock.json ./
RUN npm ci --legacy-peer-deps

# Build application
COPY . .
RUN npm run build

# Production stage
FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Copy node_modules from builder to avoid reinstalling
COPY --from=builder /app/node_modules ./node_modules

# Copy built application from builder
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/app ./app
COPY --from=builder /app/src ./src

# Copy config files needed for dev/build
COPY next.config.ts tsconfig.json ./

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=10s --timeout=5s --retries=5 --start-period=15s \
    CMD wget --quiet --tries=1 --spider http://localhost:3000 || exit 1

# Default to production start, but docker-compose can override with dev
CMD ["npm", "run", "start"]
