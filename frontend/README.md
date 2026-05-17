# Synapse Frontend

Modern Next.js 15 frontend for Synapse - AI Meeting Intelligence Platform.

## Tech Stack

- **Next.js 15** - React framework with app router
- **TypeScript** - Type safety
- **TailwindCSS** - Styling
- **shadcn/ui** - Component library
- **Zustand** - State management
- **React Query** - Data fetching
- **React Flow** - Graph visualization
- **Axios** - HTTP client

## Development

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Open http://localhost:3000
```

## Project Structure

```
frontend/
├── app/                 # Next.js app directory
│   ├── auth/           # Authentication pages
│   ├── dashboard/      # Dashboard pages
│   ├── workspace/      # Meeting workspace
│   ├── layout.tsx      # Root layout
│   ├── page.tsx        # Home page
│   └── globals.css     # Global styles
├── src/
│   ├── components/     # Reusable components
│   ├── hooks/          # Custom hooks
│   ├── lib/            # Utilities and API clients
│   └── store/          # Zustand stores
├── public/             # Static assets
└── package.json
```

## Environment Variables

Create `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## Building

```bash
npm run build
npm start
```
