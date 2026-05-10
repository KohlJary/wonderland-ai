import { describe, expect, test } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import App from '../src/App';

describe('App', () => {
  test('renders count starting at 0', () => {
    render(<App />);
    expect(screen.getByText('Count: 0')).toBeInTheDocument();
  });

  test('increments count on button click', () => {
    render(<App />);
    fireEvent.click(screen.getByText('Click me'));
    expect(screen.getByText('Count: 1')).toBeInTheDocument();
  });
});
