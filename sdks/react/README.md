# Gabber React SDK

Hooks and provider for React apps.

## Install

```bash
npm install @gabber/client-react
```

## Quickstart

```tsx
import { EngineProvider, useEngine } from '@gabber/client-react'

export function App() {
  return (
    <EngineProvider>
      <Main />
    </EngineProvider>
  )
}

function Main() {
  const { connect, connectionState } = useEngine()

  useEffect(() => {
    connect({ url: 'your-gabber-url', token: 'your-token' })
  }, [connect])

  return <div>State: {connectionState}</div>
}
```

See `src/` for hooks like `usePad`, `usePropertyPad`, `useSourcePad`.