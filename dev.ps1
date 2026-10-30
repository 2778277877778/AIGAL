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
    [ValidateSet('run', 'lint', 'compile', 'test', 'shots', 'distribute')]
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
    'shots' {
        ## 界面截图回归。这份用例平时放在 tests\shots\ 下 —— 不在 game\ 里，
        ## Ren'Py 不会加载，默认链绝不会被它拖红（基准图跟 DPI / 字体绑死，
        ## 换台机器就飘）。只有这条命令才临时拷进 game\ 跑一次，跑完连 .rpyc 一起删。
        ##
        ## .\dev.ps1 shots            比对
        ## .\dev.ps1 shots overwrite  重写基准图（改过版式必须跑一次）
        ##
        ## 为什么用 Start-Process 轮询：Ren'Py 的测试跑完不会自己退，会停回主菜单；
        ## 直接 & 调用会一直挂着。所以盯着输出文件等 Status 行，见到就掐掉进程。
        $src = Join-Path $repo 'tests\shots\ui_shots.rpy'
        $dst = Join-Path $repo 'game\__shots_ui.rpy'
        $out = Join-Path $env:TEMP 'aigal_shots.log'

        if (-not (Test-Path $src)) {
            Write-Host "找不到 $src" -ForegroundColor Red
            exit 1
        }

        Remove-Item $out -Force -ErrorAction SilentlyContinue
        Copy-Item $src $dst -Force

        try {
            $argList = @((Join-Path $sdk 'renpy.py'), $repo, 'test', 'ui_shot')
            if ($Name -eq 'overwrite') {
                $argList += '--overwrite-screenshots'
                Write-Host "重写基准图：tests\screenshots\*.png" -ForegroundColor Yellow
            }

            $proc = Start-Process -FilePath $py -ArgumentList $argList -WindowStyle Hidden -PassThru `
                -RedirectStandardOutput $out -RedirectStandardError ($out + '.err')

            $deadline = (Get-Date).AddSeconds(180)
            while (-not $proc.HasExited -and (Get-Date) -lt $deadline) {
                Start-Sleep -Milliseconds 300
                if ((Test-Path $out) -and (Select-String -Path $out -Pattern 'Status: (PASSED|FAILED|SKIPPED)' -Quiet)) {
                    Start-Sleep -Milliseconds 500
                    break
                }
            }
            if (-not $proc.HasExited) { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue }

            ## 只印到 Status 行为止：后面那段是 exit 触发的 QuitException 收尾，
            ## 每次印出来会让人以为挂了。
            if (Test-Path $out) {
                foreach ($line in (Get-Content $out -Encoding UTF8)) {
                    Write-Host $line
                    if ($line -match 'Status: (PASSED|FAILED|SKIPPED)') { break }
                }
            }

            $report = if (Test-Path $out) { Get-Content $out -Encoding UTF8 -Raw } else { '' }
            if ($report -match 'Status: PASSED') { exit 0 }

            Write-Host ""
            Write-Host "!! 截图回归失败。差异图在 tests\screenshots\*.new.png / *.diff.png；改了版式就跑 .\dev.ps1 shots overwrite" -ForegroundColor Red
            ($report -split "`n") | Select-String -Pattern 'pixel difference|size mismatch|Status:|Error' |
                Select-Object -First 6 | ForEach-Object { Write-Host ("   " + $_) -ForegroundColor Red }
            exit 1
        }
        finally {
            ## .rpy 和 .rpyc 都要删：只剩 .rpyc 的脚本 Ren'Py 照样加载
            Remove-Item $dst -Force -ErrorAction SilentlyContinue
            Remove-Item ($dst + 'c') -Force -ErrorAction SilentlyContinue
        }
    }
    'distribute' {
        & $py (Join-Path $sdk 'renpy.py') $repo distribute
    }
    default {
        ## 人物卡 / 提示词的计数与 id 一致性（文案策划 的检查器）。
        ## 跑在 lint 之前：计数漂了就没必要再看脚本。
        if ($Command -in @('lint', 'test')) {
            if (Get-Command python -ErrorAction SilentlyContinue) {
                $cardOut = & python (Join-Path $repo 'tests\check_cards.py') 2>&1
                $cardOut | ForEach-Object { Write-Host $_ }
                if ($LASTEXITCODE -ne 0) {
                    Write-Host "!! 人物卡/提示词检查器失败：python tests/check_cards.py" -ForegroundColor Red
                    exit 1
                }
            }
            else {
                Write-Host "跳过人物卡检查器：PATH 里没有 python" -ForegroundColor Yellow
            }
        }

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
