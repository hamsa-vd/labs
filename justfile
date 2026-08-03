set shell := ["zsh", "-lic"]

install:
    pnpm install

ascend-dev:
    pnpm --filter @labs/ascend dev

ascend-check:
    pnpm --filter @labs/ascend check

ascend-test:
    pnpm --filter @labs/ascend test

ascend-build:
    pnpm --filter @labs/ascend build
