import type { Config } from "tailwindcss";

export default {
  content: ["./client/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        /* ===== GREEN ===== */
        green: {
          DEFAULT: "hsla(var(--green-default))", // #1CC53C
          "semi-dark": "hsla(var(--green-semi-dark))", // #16A02D
          dark: "hsla(var(--green-dark))", // #158F2C
        },

        /* ===== BACKGROUNDS ===== */
        bg: {
          "green-transparent": "hsla(var(--bg-green-transparent))", // #1CC53C 25%
          "light-green": "hsla(var(--bg-light-green))", // #DCFCE7
          "default-light-field": "hsla(var(--bg-default-light-field))", // #9CA3AF 5%
          "light-grey": "hsla(var(--bg-light-grey))", // #DEDEEA
          "ultra-light-grey": "hsla(var(--bg-ultra-light-grey))", // #FBFBFB
          "medium-gray": "hsla(var(--bg-medium-gray))", // #9CA3AF 50%
          "yellow": "hsla(var(--bg-yellow))", // #FFE947 50%
        },

        /* ===== BORDERS ===== */
        border: {
          DEFAULT: "hsla(var(--border-default))", // #BDBDCC
          green: "hsla(var(--border-green))", // #158F2C
        },

        /* ===== TEXT ===== */
        text: {
          primary: "hsla(var(--text-primary))", // #343B46
          secondary: "hsla(var(--text-secondary))", // #667285
          tertiary: "hsla(var(--text-tertiary))", // #9CA3AF
        },

        /* ===== DARK ===== */
        dark: {
          DEFAULT: "hsla(var(--dark-default))", // #1F1F1F
          transparent: "hsla(var(--dark-default-transparent))", // #1F1F1F 90%
        },

        /* ===== COLORFUL ===== */
        red: {
          DEFAULT: "hsla(var(--red-default))", // #EF4444
          transparent: "hsla(var(--red-transparent))", // #EF4444 90%
          "light-transparent": "hsla(var(--red-light-transparent))", // #EF4444 30%
        },
        blue: {
          DEFAULT: "hsla(var(--blue-default))", // #3B82F6
          transparent: "hsla(var(--blue-transparent))", // #3B82F6 50%
        },
        yellow: {
          DEFAULT: "hsla(var(--yellow-default))", // #FFE947
        },

        /* ===== BASE ===== */
        white: "hsla(var(--white))", // #FFFFFF
        black: "hsla(var(--black))", // #000000
        
        /* ===== DIAGRAM ===== */
        diagram: {
          gray: "hsla(var(--diagram-gray))", // #8e8e8e
          orange: "hsla(var(--diagram-orange))", // #FFA73B
          purple: "hsla(var(--diagram-purple))", // #D53DFF
          red: "hsla(var(--diagram-red))", // #FF5e3e
          blue: "hsla(var(--diagram-blue))", // #3d3dff
          cyan: "hsla(var(--diagram-cyan))", // #6EDFF2
          pink: "hsla(var(--diagram-pink))", // #e65cb3
          violet: "hsla(var(--diagram-violet))", // #8b00ff
        },
        /* ===== TABLE ===== */
        table: {
          "header-bg": "hsla(var(--table-header-bg))", // #E3E3F1
          "row-even-bg": "hsla(var(--table-row-even-bg))", // #F3F3FD
          "hovered-row":"hsla(var(--table-hovered-row))", //#F7F7FD
        },
      },
    },
  },
  plugins: [],
} satisfies Config;
