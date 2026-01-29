'use client';

import { useRef, useEffect } from 'react';
import styles from './ArticleDisplay.module.css';

interface ArticleDisplayProps {
  htmlContent: string;
}

export default function ArticleDisplay({ htmlContent }: ArticleDisplayProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (containerRef.current && htmlContent) {
      containerRef.current.innerHTML = htmlContent;
    }
  }, [htmlContent]);

  if (!htmlContent) {
    return null;
  }

  return (
    <div className={styles.container}>
      <div ref={containerRef} className={styles.content} />
    </div>
  );
}
