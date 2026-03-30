import type { Config } from "tailwindcss";

export default {
  content: ["./client/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        /* Базовые */
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        
        /* Тексты */
        text: {
          primary: "hsl(var(--text-primary))",
          secondary: "hsl(var(--text-secondary))",
          tertiary: "hsl(var(--text-tertiary))",
          inactive: "hsl(var(--text-inactive))",
        },
        
        /* Границы */
        border: {
          DEFAULT: "hsl(var(--border-default))",
          green: "hsl(var(--border-green))",
          dark: "hsl(var(--text-primary))",
        },
        
        /* Зеленый */
        green: {
          DEFAULT: "hsl(var(--green))",
          sidebar: "hsla(var(--green-sidebar-bg))",
          active: "hsla(var(--green-sidebar-active))",
        },
        
        /* Красный и синий */
        red: "hsl(var(--red))",
        blue: "hsl(var(--blue))",
        
        /* Состояния */
        input: {
          focus: "hsla(var(--input-focus-ring))",
        },
        bg: {
          disabled: "hsla(var(--bg-disabled))",
          status: "hsl(var(--bg-status))",
        },
        
        /* Черный */
        black: "hsl(var(--black))",
      },
    },
  },
  plugins: [],
} satisfies Config;