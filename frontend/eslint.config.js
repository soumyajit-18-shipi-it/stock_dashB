import js from '@eslint/js';
import globals from 'globals';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import tseslint from 'typescript-eslint';
import importPlugin from 'eslint-plugin-import';
import tsPlugin from '@typescript-eslint/eslint-plugin';

export default tseslint.config(
  { ignores: ['dist', 'node_modules', 'coverage', '*.tsbuildinfo'] },
  {
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
      parserOptions: {
        project: ['./tsconfig.app.json', './tsconfig.node.json'],
        tsconfigRootDir: import.meta.dirname,
      },
    },
    settings: {
      'import/resolver': {
        typescript: {
          project: ['./tsconfig.app.json', './tsconfig.node.json'],
        },
        node: {
          extensions: ['.ts', '.tsx', '.js', '.jsx', '.json'],
        },
      },
      'import/parsers': {
        '@typescript-eslint/parser': ['.ts', '.tsx'],
      },
    },
    plugins: {
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
      import: importPlugin,
      '@typescript-eslint': tsPlugin,
    },
    rules: {
      ...js.configs.recommended.rules,
      ...reactHooks.configs.recommended.rules,
      ...importPlugin.configs.recommended.rules,
      ...importPlugin.configs.typescript.rules,
      ...tseslint.configs.recommended.reduce((acc, config) => ({ ...acc, ...config.rules }), {}),

      'react-refresh/only-export-components': [
        'warn',
        { allowConstantExport: true },
      ],

      // ---- quality-of-life additions ----
      // Block console.log/console.debug; allow warn/error/info (proper logging).
      'no-console': ['error', { allow: ['warn', 'error', 'info'] }],
      // Hard-fail on `debugger;` statements.
      'no-debugger': 'error',
      // Disable base rule so TS strict (noUnusedLocals/Parameters) governs it,
      // and bridge the TS rule to honour `_`-prefixed identifiers.
      'no-unused-vars': 'off',
      '@typescript-eslint/no-unused-vars': [
        'error',
        {
          argsIgnorePattern: '^_',
          varsIgnorePattern: '^_',
          caughtErrorsIgnorePattern: '^_',
        },
      ],
      // Encourage consistent import ordering.
      'import/order': [
        'warn',
        {
          groups: [
            'builtin',
            'external',
            'internal',
            ['parent', 'sibling', 'index'],
            'type',
          ],
          'newlines-between': 'always',
          alphabetize: { order: 'asc', caseInsensitive: true },
        },
      ],
      // Circular dependency detection - disabled due to resolver issues
      'import/no-cycle': 'off',
      // Prevent useless path segments
      'import/no-useless-path-segments': 'error',
      // Prevent extraneous dependencies
      'import/no-extraneous-dependencies': [
        'error',
        {
          devDependencies: [
            '**/*.{test,spec}.{ts,tsx}',
            'src/test/**',
            'vite.config.ts',
            'vitest.config.ts',
          ],
        },
      ],
      // Prevent default exports (prefer named exports)
      'import/prefer-default-export': 'off',
      // Ensure all imports are used (warn only)
      'import/no-unused-modules': 'warn',
    },
  },
  // Test files: relax console + no-unused to allow fixture code.
  {
    files: ['**/*.{test,spec}.{ts,tsx}', 'src/test/**/*.{ts,tsx}'],
    rules: {
      'no-console': 'off',
      'import/no-extraneous-dependencies': 'off',
    },
  }
);