'use client';

import { useState } from 'react';
import styles from './SEOMetadata.module.css';

interface SEOMetadataProps {
  metadata: any;
}

export default function SEOMetadata({ metadata }: SEOMetadataProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [copied, setCopied] = useState(false);

  if (!metadata) {
    return null;
  }

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(metadata, null, 2));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h3>SEO Metadata</h3>
        <div className={styles.actions}>
          <button onClick={handleCopy} className={styles.copyButton}>
            {copied ? 'Copied!' : 'Copy JSON'}
          </button>
          <button 
            onClick={() => setIsExpanded(!isExpanded)} 
            className={styles.toggleButton}
          >
            {isExpanded ? 'Collapse' : 'Expand'}
          </button>
        </div>
      </div>
      
      {isExpanded ? (
        <pre className={styles.json}>{JSON.stringify(metadata, null, 2)}</pre>
      ) : (
        <div className={styles.summary}>
          <div className={styles.item}>
            <strong>Title:</strong> {metadata.title || 'N/A'}
          </div>
          <div className={styles.item}>
            <strong>Description:</strong> {metadata.description || 'N/A'}
          </div>
          <div className={styles.item}>
            <strong>Keywords:</strong> {metadata.keywords?.join(', ') || 'N/A'}
          </div>
        </div>
      )}
    </div>
  );
}
