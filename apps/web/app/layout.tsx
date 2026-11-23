import type { Metadata } from 'next';
import './globals.css';
export const metadata: Metadata = {
  title: 'AI Music Video Studio',
  description: 'Studio video âm nhạc local',
};
export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <body>{children}</body>
    </html>
  );
}
