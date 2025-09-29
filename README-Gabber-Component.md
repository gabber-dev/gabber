# Gabber NextJS Component

A self-contained React component that can be dropped into any NextJS project to integrate with the Gabber streaming platform.

## Features

- 🚀 **Self-contained** - No external dependencies except the Gabber React SDK
- 🔄 **Real-time streaming** - Audio and video streaming with WebRTC
- 📱 **Responsive UI** - Clean, modern interface with Tailwind CSS
- 🔧 **Flexible configuration** - Works with both graphs and app IDs
- 🧪 **Echo functionality** - Built-in echo component for testing
- 📦 **TypeScript support** - Full type safety and IntelliSense

## Quick Start

### 1. Install Dependencies

```bash
npm install @gabber/client-react
```

### 2. Copy the Component

Copy the `gabber-nextjs-component.tsx` file to your NextJS project:

```bash
cp gabber-nextjs-component.tsx your-nextjs-project/components/
```

### 3. Basic Usage

Add the component to any page in your NextJS app:

```tsx
import GabberComponent from '../components/gabber-nextjs-component';

export default function HomePage() {
  return (
    <div className="container mx-auto p-4">
      <h1>My App</h1>

      {/* Basic usage with echo functionality */}
      <GabberComponent />
    </div>
  );
}
```

### 4. Advanced Configuration

```tsx
import GabberComponent from '../components/gabber-nextjs-component';

export default function AdvancedPage() {
  return (
    <div className="container mx-auto p-4">
      <h1>Advanced Gabber Setup</h1>

      {/* Using a custom graph */}
      <GabberComponent
        apiUrl="https://your-gabber-instance.com"
        runId="my-custom-run"
        graph={yourCustomGraph}
        showDebug={true}
      />

      {/* Using an app ID */}
      <GabberComponent
        appId="your-app-id"
        runId="my-app-run"
        apiUrl="https://your-gabber-instance.com"
      />
    </div>
  );
}
```

## Configuration Options

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `apiUrl` | `string` | `"http://localhost:8001"` | Your Gabber API endpoint |
| `runId` | `string` | `"demo-run"` | Unique identifier for this session |
| `appId` | `string?` | `undefined` | App ID to use instead of graph (takes precedence over graph) |
| `graph` | `any?` | `ECHO_GRAPH` | Custom graph definition |
| `showDebug` | `boolean` | `false` | Show debug information |
| `className` | `string` | `""` | Additional CSS classes |

### Using App ID

If you have a pre-configured app ID, you can use it instead of providing a graph:

```tsx
<GabberComponent
  appId="your-app-id"
  runId="my-session"
/>
```

### Using Custom Graph

You can provide your own graph definition:

```tsx
const myCustomGraph = {
  nodes: [
    // Your custom nodes here
  ]
};

<GabberComponent
  graph={myCustomGraph}
  runId="my-custom-session"
/>
```

## Echo Functionality

The component includes a built-in echo graph that streams audio and video back to you. This is perfect for testing your setup:

1. Click **"Connect"** to establish the session
2. Click **"Start Video"** to publish your webcam
3. Click **"Start Audio"** to publish your microphone
4. Click **"Start Echo"** to receive the stream back

## Development

### Local Development

If you're running Gabber locally:

```tsx
<GabberComponent
  apiUrl="http://localhost:8001"
  runId="dev-session"
/>
```

### Production

For production, use your deployed Gabber instance:

```tsx
<GabberComponent
  apiUrl="https://your-gabber-instance.com"
  appId="your-production-app-id"
  runId="prod-session"
/>
```

## Styling

The component uses Tailwind CSS classes. You can customize the appearance by:

1. **Overriding classes**: Pass a custom `className` prop
2. **Custom CSS**: Add your own styles to override the defaults
3. **Theme customization**: Modify the Tailwind classes in the component

### Example Custom Styling

```tsx
<GabberComponent
  className="max-w-2xl mx-auto border-2 border-blue-500"
/>
```

## Error Handling

The component includes built-in error handling:

- Connection errors are displayed in a red error box
- Media permission errors are caught and displayed
- Network errors show helpful messages

## Browser Support

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

## Troubleshooting

### "Connection failed" error

1. Check that your Gabber server is running
2. Verify the `apiUrl` is correct
3. Ensure CORS is configured properly on your Gabber server

### "Failed to publish video/audio"

1. Check browser permissions for camera/microphone
2. Ensure HTTPS is used in production
3. Try refreshing the page

### No audio/video stream

1. Check that the echo functionality is enabled
2. Verify your media devices are working
3. Try a different browser

## License

Apache-2.0 © [Gabber](https://gabber.dev)

## Support

For support, please visit:
- [Gabber Documentation](https://docs.gabber.dev)
- [GitHub Issues](https://github.com/gabber-ai/gabber/issues)
- [Discord Community](https://discord.gg/gabber)

## Contributing

Contributions are welcome! Please see our [Contributing Guide](https://github.com/gabber-ai/gabber/blob/main/CONTRIBUTING.md) for details.


