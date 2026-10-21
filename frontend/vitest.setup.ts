import '@testing-library/jest-dom';
import { vi } from 'vitest';
import { expect, afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

Element.prototype.scrollIntoView = vi.fn();

declare global {
  namespace Vi {
    interface Mock<T = any> {
      mockResolvedValue: (value: T) => Mock<T>;
      mockRejectedValue: (value: any) => Mock<T>;
    }
  }
  
  namespace jest {
    interface Mock<T = any> {
      mockResolvedValue: (value: T) => Mock<T>;
      mockRejectedValue: (value: any) => Mock<T>;
    }
  }
}