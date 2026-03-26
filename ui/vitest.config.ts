import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    coverage: {
      enabled: true,
      provider: 'v8',
      reporter: ['text', 'html', 'text-summary'],
      include: ['src/**/*.ts']
    }
  }
});
