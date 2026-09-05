FROM node:20-slim
WORKDIR /app
RUN corepack enable
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/web/package.json apps/web/package.json
RUN pnpm install --frozen-lockfile
COPY apps/web apps/web
WORKDIR /app/apps/web
RUN pnpm build
CMD ["pnpm", "start"]
