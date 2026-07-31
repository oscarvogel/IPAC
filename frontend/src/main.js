import { createApp } from 'vue'
import '@fontsource-variable/inter'
import './style.css'
import './assets/styles/print.css'
import App from './App.vue'
import { router } from './router'

const app = createApp(App)
app.use(router)
app.mount('#app')
