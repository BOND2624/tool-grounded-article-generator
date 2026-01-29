'use client';

import { useState } from 'react';
import styles from './ArticleForm.module.css';

interface ArticleFormProps {
  onSubmit: (query: string, url?: string) => void;
  loading?: boolean;
}

export default function ArticleForm({ onSubmit, loading = false }: ArticleFormProps) {
  const [query, setQuery] = useState('');
  const [url, setUrl] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSubmit(query.trim(), url.trim() || undefined);
    }
  };

  return (
    <form onSubmit={handleSubmit} className={styles.form}>
      <div className={styles.formGroup}>
        <label htmlFor="query">Article Query *</label>
        <textarea
          id="query"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g., Write an article about Trump and the Venezuela attack"
          required
          disabled={loading}
          rows={3}
        />
      </div>
      
      <div className={styles.formGroup}>
        <label htmlFor="url">Reference URL (Optional)</label>
        <input
          id="url"
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://example.com/article"
          disabled={loading}
        />
      </div>
      
      <button type="submit" disabled={loading || !query.trim()} className={styles.button}>
        {loading ? 'Generating...' : 'Generate Article'}
      </button>
    </form>
  );
}
