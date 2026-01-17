'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import ProtectedRoute from '@/components/ProtectedRoute';
import { generateArticle, regenerateArticle, removeToken, GenerateResponse } from '@/lib/api';

export default function GeneratePage() {
  return (
    <ProtectedRoute>
      <GenerateContent />
    </ProtectedRoute>
  );
}

function GenerateContent() {
  const router = useRouter();
  const [prompt, setPrompt] = useState('');
  const [referenceUrl, setReferenceUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<GenerateResponse | null>(null);
  const [regeneratePrompt, setRegeneratePrompt] = useState('');
  const [regenerating, setRegenerating] = useState(false);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    setResult(null);

    console.log('Starting article generation...');
    console.log('Prompt:', prompt);
    console.log('Reference URL:', referenceUrl);

    try {
      const response = await generateArticle({
        prompt,
        reference_url: referenceUrl || undefined,
      });
      console.log('Article generated successfully:', response);
      setResult(response);
    } catch (err: any) {
      console.error('Generation error:', err);
      setError(err.message || 'Failed to generate article');
    } finally {
      setLoading(false);
    }
  };

  const handleRegenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!result) return;

    setError('');
    setRegenerating(true);

    try {
      const response = await regenerateArticle({
        existing_article_json: result.article_json,
        refinement_prompt: regeneratePrompt,
      });
      setResult(response);
      setRegeneratePrompt('');
    } catch (err: any) {
      setError(err.message || 'Failed to regenerate article');
    } finally {
      setRegenerating(false);
    }
  };

  const handleDownload = () => {
    if (!result) return;

    const blob = new Blob([result.rendered_html], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${result.article_json.title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.html`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleLogout = () => {
    removeToken();
    router.push('/login');
  };

  return (
    <main className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Article Generator</h1>
          <button
            onClick={handleLogout}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Logout
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column: Form */}
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold mb-4">Generate Article</h2>
              
              {error && (
                <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                  {error}
                </div>
              )}

              <form onSubmit={handleGenerate} className="space-y-4">
                <div>
                  <label htmlFor="prompt" className="block text-sm font-medium text-gray-700 mb-2">
                    Article Prompt <span className="text-red-500">*</span>
                  </label>
                  <textarea
                    id="prompt"
                    rows={6}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    placeholder="e.g., Write an article about the benefits of renewable energy"
                  />
                </div>

                <div>
                  <label htmlFor="referenceUrl" className="block text-sm font-medium text-gray-700 mb-2">
                    Reference URL (Optional)
                  </label>
                  <input
                    id="referenceUrl"
                    type="url"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    value={referenceUrl}
                    onChange={(e) => setReferenceUrl(e.target.value)}
                    placeholder="https://example.com/article"
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? 'Generating...' : 'Generate Article'}
                </button>
              </form>
            </div>

            {/* Regeneration Form */}
            {result && (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-semibold mb-4">Regenerate Article</h2>
                <form onSubmit={handleRegenerate} className="space-y-4">
                  <div>
                    <label htmlFor="regeneratePrompt" className="block text-sm font-medium text-gray-700 mb-2">
                      Refinement Instructions
                    </label>
                    <textarea
                      id="regeneratePrompt"
                      rows={4}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      value={regeneratePrompt}
                      onChange={(e) => setRegeneratePrompt(e.target.value)}
                      placeholder="e.g., Make it more technical, add more examples, focus on recent developments"
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={regenerating || !regeneratePrompt.trim()}
                    className="w-full py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {regenerating ? 'Regenerating...' : 'Regenerate'}
                  </button>
                </form>
              </div>
            )}
          </div>

          {/* Right Column: Results */}
          <div className="space-y-6">
            {result && (
              <>
                {/* Article Preview */}
                <div className="bg-white rounded-lg shadow p-6">
                  <div className="flex justify-between items-center mb-4">
                    <h2 className="text-xl font-semibold">Generated Article</h2>
                    <button
                      onClick={handleDownload}
                      className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700"
                    >
                      Download HTML
                    </button>
                  </div>
                  
                  <div className="border-b mb-4 pb-4">
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                      {result.article_json.title}
                    </h3>
                    <p className="text-sm text-gray-600 mb-2">
                      {result.article_json.summary}
                    </p>
                  </div>

                  <div className="space-y-4 max-h-96 overflow-y-auto">
                    {result.article_json.sections && result.article_json.sections.length > 0 ? (
                      result.article_json.sections.map((section, idx) => (
                        <div key={idx} className="border-b pb-4 last:border-b-0">
                          <h4 className="font-semibold text-gray-800 mb-2">
                            {section.heading || 'Untitled Section'}
                          </h4>
                          <p 
                            className="text-sm text-gray-700 whitespace-pre-wrap"
                            dangerouslySetInnerHTML={{
                              __html: (() => {
                                let content = section.content || 'No content available';
                                // Escape HTML first
                                content = content
                                  .replace(/&/g, '&amp;')
                                  .replace(/</g, '&lt;')
                                  .replace(/>/g, '&gt;')
                                  .replace(/"/g, '&quot;')
                                  .replace(/'/g, '&#x27;');
                                // Convert markdown to HTML
                                content = content.replace(/\*\*([^*]+?)\*\*/g, '<strong>$1</strong>');
                                content = content.replace(/(?<!\*)\*([^*]+?)\*(?!\*)/g, '<em>$1</em>');
                                // Restore HTML tags we just added
                                content = content.replace(/&lt;strong&gt;/g, '<strong>');
                                content = content.replace(/&lt;\/strong&gt;/g, '</strong>');
                                content = content.replace(/&lt;em&gt;/g, '<em>');
                                content = content.replace(/&lt;\/em&gt;/g, '</em>');
                                return content;
                              })()
                            }}
                          />
                          {section.sources && section.sources.length > 0 && (
                            <div className="mt-2">
                              <p className="text-xs font-medium text-gray-500 mb-1">
                                Sources for "{section.heading || 'this section'}":
                              </p>
                              <ul className="text-xs space-y-1.5">
                                {section.sources.map((source, sIdx) => {
                                  // Format URL for display - extract domain and show readable format
                                  let displayText = source;
                                  let domain = '';
                                  try {
                                    const url = new URL(source);
                                    domain = url.hostname.replace('www.', '');
                                    // Show domain + first part of path
                                    const pathParts = url.pathname.split('/').filter(p => p);
                                    const path = pathParts.length > 0 
                                      ? '/' + pathParts[0] + (pathParts.length > 1 ? '/...' : '')
                                      : '';
                                    displayText = domain + path;
                                  } catch {
                                    // If URL parsing fails, just truncate
                                    if (source.length > 60) {
                                      displayText = source.substring(0, 60) + '...';
                                    }
                                  }
                                  
                                  return (
                                    <li key={sIdx} className="flex items-start gap-2">
                                      <span className="text-gray-400 mt-0.5">•</span>
                                      <a 
                                        href={source} 
                                        target="_blank" 
                                        rel="noopener noreferrer" 
                                        className="text-blue-600 hover:text-blue-800 hover:underline break-all flex-1"
                                        title={`${source} - Reference for: ${section.heading || 'this section'}`}
                                      >
                                        <span className="font-medium">{domain}</span>
                                        {displayText !== domain && (
                                          <span className="text-gray-600">{displayText.replace(domain, '')}</span>
                                        )}
                                      </a>
                                    </li>
                                  );
                                })}
                              </ul>
                            </div>
                          )}
                        </div>
                      ))
                    ) : (
                      <div className="text-center text-gray-500 py-8">
                        <p>No sections available. The article structure may be incomplete.</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* SEO Metadata */}
                <div className="bg-white rounded-lg shadow p-6">
                  <h2 className="text-xl font-semibold mb-4">SEO Metadata</h2>
                  <div className="space-y-3 text-sm">
                    <div>
                      <span className="font-medium text-gray-700">Meta Title:</span>
                      <p className="text-gray-600">{result.seo_json.meta_title}</p>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">Meta Description:</span>
                      <p className="text-gray-600">{result.seo_json.meta_description}</p>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">Keywords:</span>
                      <p className="text-gray-600">{result.seo_json.keywords && result.seo_json.keywords.length > 0 ? result.seo_json.keywords.join(', ') : 'None'}</p>
                    </div>
                    {result.seo_json.canonical_url && (
                      <div>
                        <span className="font-medium text-gray-700">Canonical URL:</span>
                        <p className="text-gray-600">{result.seo_json.canonical_url}</p>
                      </div>
                    )}
                  </div>
                </div>
              </>
            )}

            {!result && !loading && (
              <div className="bg-white rounded-lg shadow p-6 text-center text-gray-500">
                <p>Generated articles will appear here</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
