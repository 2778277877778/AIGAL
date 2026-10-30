<#
.SYNOPSIS
    找 Ren'Py SDK 并跑本工程。依赖清单见 依赖.md。

.EXAMPLE
    .\dev.ps1 lint
    .\dev.ps1 test
    .\dev.ps1 run
    .\dev.ps1 compile
    .\dev.ps1 distribute
#>
param(
    [Parameter(Position = 0)]
    [ValidateSet('run', 'lint', 'compile', 'test', 'distribute')]
    [string]$Command = 'lint',

    # test 用：只跑某个 testcase
    [Parameter(Position = 1)]
    [string]$Name = ''
)

$ErrorActionPreference = 'Stop'
$repo = $PSScriptRoot

function Find-Sdk {
    $candidates = @()

    if ($env:RENPY_SDK) { $candidates += $env:RENPY_SDK }
    $candidates += (Join-Path (Split-Path $repo -Parent) 'tools\renpy-8.5.3-sdk')
    $candidates += (Join-Path (Split-Path $repo -Parent) 'renpy-8.5.3-sdk')
    $candidates += 'C:\renpy-8.5.3-sdk'
    $candidates += 'D:\renpy-8.5.3-sdk'
    $candidates += (Join-Path $env:LOCALAPPDATA 'renpy-8.5.3-sdk')

    foreach ($c in $candidates) {
        if (-not $c) { continue }
        if (Test-Path (Join-Path $c 'renpy.py')) { return (Resolve-Path $c).Path }
    }

    Write-Host "没找到 Ren'Py 8.5.3 SDK。" -ForegroundColor Red
    Write-Host "下载：https://www.renpy.org/dl/8.5.3/renpy-8.5.3-sdk.zip （解压即可，不用安装）" -ForegroundColor Yellow
    Write-Host "然后二选一：" -ForegroundColor Yellow
    Write-Host '  $env:RENPY_SDK = "D:\renpy-8.5.3-sdk"'
    Write-Host "  或者把它放到  $((Split-Path $repo -Parent))\tools\renpy-8.5.3-sdk"
    exit 1
}

$sdk = Find-Sdk
$py = Join-Path $sdk 'lib\py3-windows-x86_64\python.exe'

Write-Host "SDK : $sdk"
Write-Host "工程: $repo"
Write-Host "命令: $Command"

switch ($Command) {
    'run' {
        # 沙箱里跑不了 %APPDATA% 时，调用方自己设 $env:RENPY_PATH_TO_SAVES
        & (Join-Path $sdk 'renpy.exe') $repo
    }
    'distribute' {
        & $py (Join-Path $sdk 'renpy.py') $repo distribute
    }
    default {
        $argList = @((Join-Path $sdk 'renpy.py'), $repo, $Command)
        if ($Command -eq 'test' -and $Name) { $argList += $Name }

        ## Ren'Py 的退出码不可信：lint 在 init 里抛异常也照样返回 0。
        ## 所以这里必须看输出，只看 $LASTEXITCODE 等于没测。
        $output = & $py @argList 2>&1
        $output | ForEach-Object { Write-Host $_ }
        $code = $LASTEXITCODE

        $pattern = $null
        if ($Command -in @('lint', 'compile')) {
            $pattern = 'Full traceback|^\s*Exception|Traceback \(most recent call last\)'
        }
        elseif ($Command -eq 'test') {
            ## FAILED = 用例挂了；SKIPPED = 套件压根没跑起来（init 抛异常时就是这样）
            $pattern = 'Status: FAILED|Status: SKIPPED'
        }

        if ($pattern) {
            $bad = $output | Select-String -Pattern $pattern
            if ($bad) {
                Write-Host ""
                Write-Host "!! $Command 失败：Ren'Py 的退出码是 $code，但输出里有异常/失败标记：" -ForegroundColor Red
                $bad | Select-Object -First 5 | ForEach-Object { Write-Host ("   " + $_) -ForegroundColor Red }
                exit 1
            }
        }

        exit $code
    }
}

exit $LASTEXITCODE
