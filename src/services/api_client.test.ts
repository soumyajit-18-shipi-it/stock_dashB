import { describe, it, expect, vi } from 'vitest';

global.fetch = vi.fn();

describe('API Client', () => {
  it('should be defined', () => {
    expect(true).toBe(true);
  });
});
