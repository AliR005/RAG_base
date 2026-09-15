FROM node:22-alpine AS build

WORKDIR /srv/frontend
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:22-alpine

WORKDIR /srv/frontend
ENV NODE_ENV=production
COPY --from=build /srv/frontend/package.json ./
COPY --from=build /srv/frontend/.next ./.next
COPY --from=build /srv/frontend/node_modules ./node_modules

EXPOSE 3000

CMD ["npm", "start"]
