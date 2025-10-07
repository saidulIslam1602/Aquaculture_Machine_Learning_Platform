# Aquaculture ML Platform - Frontend Dashboard

React + TypeScript dashboard for the Aquaculture ML Platform.

## Technology Stack

- **React 18** - UI library
- **TypeScript 5** - Type safety
- **Vite** - Build tool
- **Material-UI** - Component library
- **Recharts** - Data visualization
- **React Query** - Server state management
- **Axios** - HTTP client

## Getting Started

### Prerequisites

- Node.js 18+ and npm

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
# Start development server
npm run dev

# Access at http://localhost:3000
```

### Build

```bash
# Production build
npm run build

# Preview production build
npm run preview
```

### Type Checking

```bash
npm run type-check
```

### Linting

```bash
npm run lint
```

## Docker

```bash
# Build Docker image
docker build -f ../infrastructure/docker/Dockerfile.frontend -t aquaculture-frontend .

# Run container
docker run -p 3000:80 aquaculture-frontend
```

## Features

- Authentication with JWT
- Real-time dashboard metrics
- ML inference interface
- Task monitoring
- Responsive design
- Dark mode support

## Project Structure

```
frontend/
├── src/
│   ├── components/     # Reusable components
│   ├── pages/          # Page components
│   ├── services/       # API clients
│   ├── hooks/          # Custom hooks
│   ├── contexts/       # React contexts
│   ├── types/          # TypeScript types
│   └── utils/          # Utilities
├── public/             # Static assets
└── index.html          # Entry HTML
```

## Note

TypeScript errors about missing modules will resolve after running `npm install`.
This is expected behavior before dependencies are installed.
