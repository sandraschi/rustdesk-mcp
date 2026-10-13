# Per-repo fleet start config for rustdesk-mcp
# Edit ports/backend target here - start.ps1 is fleet-standard.
@{
    Name         = 'rustdesk-mcp'
    BackendPort  = 10805
    FrontendPort = 10804
    HealthPath   = '/health'
    WebRoot      = 'web_sota'
    Backend = @{
        Kind          = 'uvicorn'
        UvicornTarget = 'rustdesk_mcp.server:app'
        SyncExtras    = @('dev')
        SyncOnStart  = $true
        Env           = @{ WEB_PORT = '10805' }
    }
    Frontend = @{
        Kind           = 'vite-npm'
        PackageManager = 'npm'
        PortEnvVar     = 'VITE_PORT'
        ApiTargetEnv   = 'VITE_API_TARGET'
    }
}
