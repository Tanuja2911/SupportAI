FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

RUN npm run build

EXPOSE 5173

CMD ["sh", "-c", "npx serve -s dist -l ${PORT:-5173}"]

