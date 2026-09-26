FROM node:20-alpine

WORKDIR /app

ARG VITE_API_URL=
ENV VITE_API_URL=${VITE_API_URL}

COPY package*.json ./
RUN npm ci

COPY . .

RUN npm run build

EXPOSE 5173

CMD ["sh", "-c", "npx serve -s dist -l ${PORT:-5173}"]

