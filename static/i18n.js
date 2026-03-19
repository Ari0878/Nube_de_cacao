// Sistema de internacionalización (i18n) simple
class I18n {
    constructor() {
        this.translations = {};
        this.fallbackLang = 'es';
        this.currentLang = localStorage.getItem('idioma') || 'es';
    }

    async init() {
        try {
            const response = await fetch('/static/translations.json');
            this.translations = await response.json();
            return true;
        } catch (error) {
            console.error('Error loading translations:', error);
            return false;
        }
    }

    setLanguage(lang) {
        if (this.translations[lang]) {
            this.currentLang = lang;
            localStorage.setItem('idioma', lang);
            return true;
        }
        return false;
    }

    t(key) {
        const keys = key.split('.');
        let value = this.translations[this.currentLang];
        
        for (const k of keys) {
            if (value && typeof value === 'object') {
                value = value[k];
            } else {
                value = undefined;
                break;
            }
        }

        // Fallback al idioma por defecto si no se encuentra
        if (value === undefined) {
            value = this.translations[this.fallbackLang];
            for (const k of keys) {
                if (value && typeof value === 'object') {
                    value = value[k];
                } else {
                    value = key; // Si tampoco está en fallback, mostrar la key
                    break;
                }
            }
        }

        return value || key;
    }

    translatePage() {
        // Traducir elementos con atributo data-i18n
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.getAttribute('data-i18n');
            element.textContent = this.t(key);
        });

        // Traducir placeholders
        document.querySelectorAll('[data-i18n-placeholder]').forEach(element => {
            const key = element.getAttribute('data-i18n-placeholder');
            element.placeholder = this.t(key);
        });

        // Traducir titles
        document.querySelectorAll('[data-i18n-title]').forEach(element => {
            const key = element.getAttribute('data-i18n-title');
            element.title = this.t(key);
        });
    }

    getCurrentLanguage() {
        return this.currentLang;
    }
}

// Instancia global
const i18n = new I18n();

// Añadimos soporte para tema claro/oscuro usando localStorage y preferencia del sistema
I18n.prototype.getTheme = function() {
    return localStorage.getItem('theme') || 'auto';
};

I18n.prototype.setTheme = function(theme) {
    if (!theme) return;
    localStorage.setItem('theme', theme);
    this.applyTheme(theme);
};

I18n.prototype.applyTheme = function(theme) {
    const resolvedTheme = theme || this.getTheme();

    if (resolvedTheme === 'auto') {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        document.body.classList.toggle('dark-mode', prefersDark);
    } else {
        document.body.classList.toggle('dark-mode', resolvedTheme === 'dark');
    }
};

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', async () => {
    await i18n.init();
    i18n.translatePage();
    i18n.applyTheme(i18n.getTheme());

    // Actualizar selectores de idioma si existen
    const langSelectors = document.querySelectorAll('select[name="idioma"]');
    langSelectors.forEach(selector => {
        selector.value = i18n.getCurrentLanguage();
    });
});
