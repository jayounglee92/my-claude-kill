# Test Code Examples

Reference examples for STEP 2 (Unit) and STEP 4 (Integration). Adapt to match the project's conventions.

## Unit Test Example (STEP 2)

```typescript
// __tests__/components/EventRegistrationForm.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { EventRegistrationForm } from '@/components/EventRegistrationForm';

describe('EventRegistrationForm', () => {
  it('calls onSubmit with name after filling and submitting', async () => {
    const onSubmit = vi.fn();
    render(<EventRegistrationForm onSubmit={onSubmit} />);

    await userEvent.type(screen.getByLabelText('Name'), 'John');
    await userEvent.click(screen.getByRole('button', { name: 'Submit' }));

    expect(onSubmit).toHaveBeenCalledWith({ name: 'John' });
  });

  it('does not submit when name is empty', async () => {
    const onSubmit = vi.fn();
    render(<EventRegistrationForm onSubmit={onSubmit} />);

    await userEvent.click(screen.getByRole('button', { name: 'Submit' }));

    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByText('Please enter your name')).toBeInTheDocument();
  });
});
```

## Integration Test Example (STEP 4)

```typescript
// __tests__/integration/event-registration.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { server } from '@/mocks/server';
import { http, HttpResponse } from 'msw';
import { EventRegistrationPage } from '@/app/events/[id]/register/page';

describe('Event registration integration', () => {
  it('navigates to confirmation on successful registration', async () => {
    server.use(
      http.post('/api/events/123/register', () =>
        HttpResponse.json({ success: true })
      )
    );

    render(<EventRegistrationPage params={{ id: '123' }} />);
    await userEvent.type(screen.getByLabelText('Name'), 'John');
    await userEvent.click(screen.getByRole('button', { name: 'Submit' }));

    await waitFor(() => {
      expect(screen.getByText('Registration complete')).toBeInTheDocument();
    });
  });

  it('displays error message on API failure', async () => {
    server.use(
      http.post('/api/events/123/register', () =>
        HttpResponse.json({ error: 'Registration closed' }, { status: 400 })
      )
    );

    render(<EventRegistrationPage params={{ id: '123' }} />);
    await userEvent.type(screen.getByLabelText('Name'), 'John');
    await userEvent.click(screen.getByRole('button', { name: 'Submit' }));

    await waitFor(() => {
      expect(screen.getByText('Registration closed')).toBeInTheDocument();
    });
  });
});
```
