'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import ProtectedRoute from '@/components/ProtectedRoute';
import ArticleForm from '@/components/ArticleForm';
import ArticleDisplay from '@/components/ArticleDisplay';
import SEOMetadata from '@/components/SEOMetadata';
import { api } from '@/lib/api';
import { removeAuthToken } from '@/lib/auth';
import styles from './page.module.css';

export default function DashboardPage() {
  const router = useRouter();
  const [articleData, setArticleData] = useState<any>(null);
  const [seoMetadata, setSeoMetadata] = useState<any>(null);
  const [htmlContent, setHtmlContent] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [regeneratePrompt, setRegeneratePrompt] = useState<string>('');
  const [regenerating, setRegenerating] = useState(false);

  const handleGenerate = async (query: string, url?: string) => {
    setLoading(true);
    setError('');
    setArticleData(null);
    setSeoMetadata(null);
    setHtmlContent('');

    try {
      const response = await api.generateArticle({ query, url });
      setArticleData(response.article_json);
      setSeoMetadata(response.seo_metadata_json);
      setHtmlContent(response.html_content);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate article. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleRegenerate = async () => {
    if (!articleData || !regeneratePrompt.trim()) {
      return;
    }

    setRegenerating(true);
    setError('');

    try {
      const response = await api.regenerateArticle({
        article_json: articleData,
        prompt: regeneratePrompt.trim(),
      });
      setArticleData(response.article_json);
      setSeoMetadata(response.seo_metadata_json);
      setHtmlContent(response.html_content);
      setRegeneratePrompt('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to regenerate article. Please try again.');
    } finally {
      setRegenerating(false);
    }
  };

  const handleDownload = () => {
    if (!htmlContent) return;

    const blob = new Blob([htmlContent], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    a.download = `article-${timestamp}.html`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleLogout = () => {
    removeAuthToken();
    router.push('/');
  };

  return (
    <ProtectedRoute>
      <div className={styles.container}>
        <header className={styles.header}>
          <h1>Article Generator Dashboard</h1>
          <button onClick={handleLogout} className={styles.logoutButton}>
            Logout
          </button>
        </header>

        <main className={styles.main}>
          <div className={styles.sidebar}>
            <ArticleForm onSubmit={handleGenerate} loading={loading} />
            
            {error && <div className={styles.error}>{error}</div>}
          </div>

          <div className={styles.content}>
            {htmlContent && (
              <>
                <div className={styles.actions}>
                  <button 
                    onClick={handleDownload} 
                    className={styles.downloadButton}
                  >
                    Download HTML
                  </button>
                </div>

                <SEOMetadata metadata={seoMetadata} />

                <ArticleDisplay htmlContent={htmlContent} />

                <div className={styles.regenerateSection}>
                  <h3>Regenerate Article</h3>
                  <div className={styles.regenerateForm}>
                    <input
                      type="text"
                      value={regeneratePrompt}
                      onChange={(e) => setRegeneratePrompt(e.target.value)}
                      placeholder="e.g., Make this more appealing to a Gen Z audience"
                      className={styles.regenerateInput}
                    />
                    <button
                      onClick={handleRegenerate}
                      disabled={regenerating || !regeneratePrompt.trim()}
                      className={styles.regenerateButton}
                    >
                      {regenerating ? 'Regenerating...' : 'Regenerate'}
                    </button>
                  </div>
                </div>
              </>
            )}

            {!htmlContent && !loading && (
              <div className={styles.emptyState}>
                <p>Generate an article to get started</p>
              </div>
            )}

            {loading && (
              <div className={styles.loadingState}>
                <p>Generating article... This may take a moment.</p>
              </div>
            )}
          </div>
        </main>
      </div>
    </ProtectedRoute>
  );
}
