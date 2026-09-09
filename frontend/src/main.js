import { createApp } from 'vue'
import './assets/styles/inter-latin.css'
import './style.css'
import './assets/styles/print.css'
import App from './App.vue'
import { router } from './router'

const app = createApp(App)
app.use(router)
app.mount('#app')
