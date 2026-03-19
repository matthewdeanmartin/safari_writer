import { App } from './app';

const canvas = document.getElementById('terminal') as HTMLCanvasElement;
const app = new App(canvas);
app.start();
