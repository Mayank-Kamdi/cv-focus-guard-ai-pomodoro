# Manual git push to GitHub
Write-Host "`n" -ForegroundColor Cyan
Write-Host "   Focus Guard - GitHub Push Setup                      " -ForegroundColor Cyan
Write-Host "   v1.0.0 - Production Ready                            " -ForegroundColor Cyan
Write-Host "`n" -ForegroundColor Cyan

# Check for GitHub CLI
$hasGH = $null -ne (Get-Command gh -ErrorAction SilentlyContinue)

if ($hasGH) {
    Write-Host " GitHub CLI found - attempting automatic setup..." -ForegroundColor Green
    gh auth login
    gh repo create focus-guard-ai-pomodoro --public --source=. --remote=origin --push 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n SUCCESS! Pushed to GitHub" -ForegroundColor Green
        exit
    }
}

Write-Host "Using manual setup..." -ForegroundColor Yellow
$repoUrl = Read-Host "Enter your GitHub repository URL (https://github.com/.../focus-guard-ai-pomodoro)"

if ([string]::IsNullOrWhiteSpace($repoUrl)) {
    Write-Host "No URL provided" -ForegroundColor Red
    exit 1
}

git remote remove origin 2>$null
git remote add origin $repoUrl
git branch -M main 2>$null
git push -u origin main

Write-Host "`n Deployment complete!" -ForegroundColor Green
Write-Host "Repository: $repoUrl" -ForegroundColor Cyan
