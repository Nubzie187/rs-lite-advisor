FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package.json ./

# Install dependencies
RUN npm install --no-audit --no-fund --legacy-peer-deps

# Copy application code
COPY . .

# Expose port
EXPOSE 5173

# Run dev server with hot reload
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]

