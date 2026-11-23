# 01 — Git: initialize and publish

## What's about to happen

Turn `papermind/` into a git repo, then publish it to GitHub.

## Why

Every change needs a commit history, and the project needs a home on GitHub
so it can be pushed to and shared from.

## What we did

**1. Initialize locally**
```
git init
git add .gitignore CLAUDE.md docs learning
git commit -m "Initialize papermind as its own git repo"
```

**2. Publish to GitHub**

The machine has two GitHub accounts logged into `gh` (`AkshayChavhan` and
`akshayvchavh`). We picked which one to publish under before doing anything:
```
gh auth status          # lists both accounts, shows which is active
```
`AkshayChavhan` was already the active account and the one we wanted, so we
published straight to it:
```
gh repo create papermind --public --source=. --remote=origin --push
```
This one command creates the GitHub repo under the active account, adds it
as the `origin` remote, and pushes `main` to it.

Result: [github.com/AkshayChavhan/papermind](https://github.com/AkshayChavhan/papermind)
