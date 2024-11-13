# React Frontend

This current frontend is a result of a migration from react-scripts to vite, which was facilitated by:
```
npm create vite@latest . -- --template react
```
Then the unneeded template files were thrown away, and the actual source files from the original react-scripts setup were migrated and partially altered to use newer React conventions.

## React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react/README.md) uses [Babel](https://babeljs.io/) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh
