import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@/lib/supabase/server';

const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000';

// Allow up to 10 minutes for workflow execution
export const maxDuration = 600;

export interface WorkflowInput {
  // Basic flow inputs
  appIdea: string;
  targetUsers: string;
  features: string;
  uiDesign: string;

  // Advanced options (optional - defaults applied by backend)
  architecture?: {
    state?: string;
    nav?: string;
    db?: string;
  };
  backend?: {
    type?: string;
  };
  codeSettings?: {
    defensive?: boolean;
    tests?: string;
    docs?: string;
  };
  quality?: {
    a11y?: string;
    performance?: string;
  };
  environment?: Record<string, string>;

  // GitHub settings
  github: {
    token: string;
    repoName: string;
    isNewRepo: boolean;
  };
}

export async function POST(request: NextRequest) {
  try {
    // Get user from Supabase session
    const supabase = await createClient();
    const { data: { user } } = await supabase.auth.getUser();

    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const body: WorkflowInput = await request.json();

    // Validate required fields
    if (!body.appIdea || !body.targetUsers || !body.features || !body.uiDesign) {
      return NextResponse.json(
        { error: 'Missing required fields: appIdea, targetUsers, features, uiDesign' },
        { status: 400 }
      );
    }

    if (!body.github?.token || !body.github?.repoName) {
      return NextResponse.json(
        { error: 'GitHub token and repository name are required' },
        { status: 400 }
      );
    }

    // Transform to backend format
    const backendPayload = {
      basic_inputs: {
        app_idea: body.appIdea,
        target_users: body.targetUsers,
        features: body.features,
        ui_design: body.uiDesign,
      },
      advanced_options: {
        architecture: body.architecture || { state: 'riverpod', nav: 'go_router', db: 'drift' },
        backend: body.backend || { type: 'offline-first' },
        code_settings: body.codeSettings || { defensive: true, tests: 'basic', docs: 'inline' },
        quality: body.quality || { a11y: 'standard', performance: 'balanced' },
        environment: body.environment || {},
      },
      github_config: {
        token: body.github.token,
        repo_name: body.github.repoName,
        create_new: body.github.isNewRepo,
      },
    };

    // First, check if backend is reachable
    try {
      const healthCheck = await fetch(`${API_BASE_URL}/health`, {
        method: 'GET',
        signal: AbortSignal.timeout(5000), // 5 second timeout for health check
      });
      if (!healthCheck.ok) {
        return NextResponse.json(
          { error: 'Backend server is not healthy. Please ensure the API server is running.' },
          { status: 503 }
        );
      }
    } catch {
      return NextResponse.json(
        { error: `Cannot connect to backend at ${API_BASE_URL}. Please ensure the API server is running.` },
        { status: 503 }
      );
    }

    // Call the FastAPI backend with user ID
    // Note: This is a long-running operation (can take several minutes)
    try {
      const response = await fetch(`${API_BASE_URL}/api/workflow/run`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Id': user.id,
        },
        body: JSON.stringify(backendPayload),
        // Use AbortSignal.timeout for 10 minute timeout
        signal: AbortSignal.timeout(10 * 60 * 1000),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        return NextResponse.json(
          { error: errorData.detail || 'Backend workflow failed', details: errorData },
          { status: response.status }
        );
      }

      const result = await response.json();
      return NextResponse.json(result);
    } catch (fetchError) {
      console.error('Workflow fetch error:', fetchError);

      if (fetchError instanceof Error) {
        const errorName = fetchError.name;
        const errorMessage = fetchError.message;

        console.error(`Error details - name: ${errorName}, message: ${errorMessage}`);

        if (errorName === 'TimeoutError' || errorName === 'AbortError') {
          return NextResponse.json(
            { error: 'Workflow timed out after 10 minutes. The app generation is taking too long. Please try with a simpler app idea.' },
            { status: 504 }
          );
        }

        // Check for connection/network errors - but note the workflow may have succeeded
        if (errorMessage.includes('fetch failed') || errorMessage.includes('ECONNREFUSED') || errorMessage.includes('socket') || errorMessage.includes('network')) {
          return NextResponse.json(
            {
              error: 'Connection to backend was interrupted. The workflow may have completed successfully - please check your GitHub repository.',
              details: errorMessage,
              hint: 'Check your GitHub account for a new repository or PR. The workflow often completes even when this error appears.'
            },
            { status: 503 }
          );
        }

        // For any other error, include details
        return NextResponse.json(
          { error: `Workflow failed: ${errorMessage}`, details: errorName },
          { status: 500 }
        );
      }
      throw fetchError;
    }
  } catch (error) {
    console.error('Workflow API error:', error);
    return NextResponse.json(
      { error: 'Internal server error', message: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
