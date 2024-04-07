# Backup server (frontend)
## commands

```sh
# install dependencies
npm ci

# start dev server
npm run dev

# build (to ../templates/)
npm run build

# lint
npm run lint:tsc
npm run lint:eslint
npm run lint:prettier

# fix
npm run fix:eslint
npm run fix:prettier
```

## 環境変数

APIサーバのアドレスに合わせて .env の VITE_SERVER を変更すること。