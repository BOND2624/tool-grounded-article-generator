'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { isAuthenticated } from '@/lib/auth';

export default function Home() {
  const router = useRouter();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) return;
    
    if (isAuthenticated()) {
      router.push('/generate');
    } else {
      router.push('/login');
    }
  }, [mounted, router]);

  return (
    <main className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <p className="text-gray-600">Loading...</p>
      </div>
    </main>
  );
}
