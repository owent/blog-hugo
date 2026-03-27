# Skill 同步脚本
# 将 .agents/skills/ 作为主副本，同步到所有 Agent 目录
# 自动扫描 .agents/skills/ 下的所有 skill 目录，无需硬编码

$agents = @(
    ".claude/skills",
    ".kilocode/skills",
    ".roo/skills"
)

$source = ".agents/skills"

Write-Host "Syncing skills from $source to all agent directories..." -ForegroundColor Green

# 动态扫描所有 skill 目录
$skills = Get-ChildItem -Path $source -Directory | Select-Object -ExpandProperty Name

if ($skills.Count -eq 0) {
    Write-Host "No skills found in $source" -ForegroundColor Yellow
    exit 0
}

Write-Host "Found skills: $($skills -join ', ')" -ForegroundColor Cyan

foreach ($agent in $agents) {
    Write-Host "`nSyncing to $agent..." -ForegroundColor Cyan
    
    # 确保目录存在
    if (-not (Test-Path $agent)) {
        New-Item -ItemType Directory -Path $agent -Force | Out-Null
        Write-Host "  Created directory: $agent" -ForegroundColor Yellow
    }
    
    foreach ($skill in $skills) {
        $sourceSkill = "$source/$skill"
        $targetSkill = "$agent/$skill"
        
        # 确保目标 skill 目录存在
        if (-not (Test-Path $targetSkill)) {
            New-Item -ItemType Directory -Path $targetSkill -Force | Out-Null
        }
        
        # 同步 SKILL.md
        if (Test-Path "$sourceSkill/SKILL.md") {
            Copy-Item "$sourceSkill/SKILL.md" "$targetSkill/SKILL.md" -Force
            Write-Host "  ✓ $skill/SKILL.md" -ForegroundColor Green
        }
        
        # 同步 references/ 目录（如果存在）
        if (Test-Path "$sourceSkill/references") {
            if (-not (Test-Path "$targetSkill/references")) {
                New-Item -ItemType Directory -Path "$targetSkill/references" -Force | Out-Null
            }
            Copy-Item "$sourceSkill/references/*" "$targetSkill/references/" -Force -Recurse
            Write-Host "  ✓ $skill/references/" -ForegroundColor Green
        }
        
        # 同步 scripts/ 目录（如果存在）
        if (Test-Path "$sourceSkill/scripts") {
            if (-not (Test-Path "$targetSkill/scripts")) {
                New-Item -ItemType Directory -Path "$targetSkill/scripts" -Force | Out-Null
            }
            Copy-Item "$sourceSkill/scripts/*" "$targetSkill/scripts/" -Force -Recurse
            Write-Host "  ✓ $skill/scripts/" -ForegroundColor Green
        }
    }
}

Write-Host "`n✓ All skills synced successfully!" -ForegroundColor Green

# 验证哈希（只验证 SKILL.md 文件）
Write-Host "`nVerifying file hashes..." -ForegroundColor Cyan

$allMatch = $true
foreach ($agent in $agents) {
    $agentMatch = $true
    foreach ($skill in $skills) {
        $sourceFile = "$source/$skill/SKILL.md"
        $targetFile = "$agent/$skill/SKILL.md"
        
        if ((Test-Path $sourceFile) -and (Test-Path $targetFile)) {
            $sourceHash = (Get-FileHash $sourceFile -Algorithm SHA256).Hash
            $targetHash = (Get-FileHash $targetFile -Algorithm SHA256).Hash
            
            if ($sourceHash -ne $targetHash) {
                Write-Host "  ✗ $agent/$skill/SKILL.md - hash mismatch!" -ForegroundColor Red
                $agentMatch = $false
                $allMatch = $false
            }
        }
    }
    
    if ($agentMatch) {
        Write-Host "  ✓ $agent - all skills verified" -ForegroundColor Green
    }
}

if ($allMatch) {
    Write-Host "`n✓ All files verified successfully!" -ForegroundColor Green
}
else {
    Write-Host "`n✗ Some files failed verification. Please check manually." -ForegroundColor Red
    exit 1
}
