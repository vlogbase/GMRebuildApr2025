module.exports = [
    {
        languageOptions: {
            ecmaVersion: 2021,
            sourceType: "script",
            globals: {
                window: "readonly",
                document: "readonly",
                console: "readonly",
                fetch: "readonly",
                FormData: "readonly",
                URLSearchParams: "readonly",
                localStorage: "readonly",
                sessionStorage: "readonly",
                alert: "readonly",
                confirm: "readonly",
                setTimeout: "readonly",
                setInterval: "readonly",
                clearTimeout: "readonly",
                clearInterval: "readonly"
            }
        },
        rules: {
            // Focus on syntax errors and critical issues
            "no-undef": "error",
            "no-unused-vars": "warn",
            "no-redeclare": "error",
            "no-unreachable": "error",
            "no-dupe-keys": "error",
            "no-duplicate-case": "error",
            "valid-typeof": "error",
            "no-unexpected-multiline": "error",
            "no-irregular-whitespace": "error"
        }
    }
];