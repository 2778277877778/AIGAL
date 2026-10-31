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
    [ValidateSet('run', 'lint', 'compile', 'test', 'diversity', 'shots', 'distribute')]
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

function Enter-RenpyLock {
    <#
    Ren'Py 的 log.txt / saves / persistent 都是共享的：同一台机器同时跑两个实例，
    第二个的 QuitException 会窜进第一个的测试，报出根本不存在的失败。
    所以在开跑前先拿一把文件锁，拿不到就排队；持有者进程已死 → 视为陈旧锁，直接接管。
    #>
    param([string]$Command)

    $path = Join-Path (Split-Path $repo -Parent) '.testlock'
    $deadline = (Get-Date).AddSeconds(120)
    $announced = $false

    while ($true) {
        try {
            $fs = [System.IO.File]::Open($path, [System.IO.FileMode]::CreateNew,
                [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
            $w = New-Object System.IO.StreamWriter($fs)
            $w.WriteLine("pid=$PID")
            $w.WriteLine("cmd=$Command")
            $w.WriteLine("at=$((Get-Date).ToString('o'))")
            $w.Flush()
            return @{ Path = $path; Stream = $fs; Writer = $w }
        }
        catch {
            $holderPid = 0
            $ageMin = 0
            try {
                $first = Get-Content $path -TotalCount 1 -ErrorAction Stop
                if ($first -match 'pid=(\d+)') { $holderPid = [int]$Matches[1] }
                $ageMin = ((Get-Date) - (Get-Item $path).LastWriteTime).TotalMinutes
            }
            catch { }

            $alive = $false
            if ($holderPid -gt 0) { $alive = [bool](Get-Process -Id $holderPid -ErrorAction SilentlyContinue) }
            ## 超过 30 分钟的锁一律视为陈旧（PID 会被系统复用，光看存活不可靠）
            if ($alive -and $ageMin -lt 30) {
                if (-not $announced) {
                    Write-Host "另一个 Ren'Py 实例在跑（PID $holderPid），排队等锁…" -ForegroundColor Yellow
                    $announced = $true
                }
                if ((Get-Date) -gt $deadline) {
                    Write-Host "等锁超过 120 秒，放弃：$path" -ForegroundColor Red
                    exit 1
                }
                Start-Sleep -Milliseconds 500
                continue
            }
            Remove-Item $path -Force -ErrorAction SilentlyContinue
        }
    }
}

function Exit-RenpyLock {
    param($Lock)
    if (-not $Lock) { return }
    try { $Lock.Writer.Dispose() } catch { }
    try { $Lock.Stream.Dispose() } catch { }
    Remove-Item $Lock.Path -Force -ErrorAction SilentlyContinue
}

$sdk = Find-Sdk
$lock = Enter-RenpyLock $Command
try {

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
        ## Ren'Py 8.5.3 没有 distribute 命令：注册过的 CLI 命令只有
        ## run / lint / compile / rmpersistent / quit（外加游戏自己注册的 test 等）。
        ## 构建逻辑在 launcher/game/distribute.rpy 的 Distributor 里，只有启动器 GUI
        ## 能驱动，所以这里只负责把启动器打开；真正构建仍然要手点一次。
        ##
        ## 不用 & 直接调用：启动器是常驻窗口，& 会一直挂着，还占着 dev.ps1 的锁。
        $launcher = Join-Path $sdk 'renpy.exe'
        Write-Host "打包没有命令行入口：Ren'Py 8.5.3 没有 distribute 命令，构建只能在启动器里做。" -ForegroundColor Yellow
        Write-Host "  1. 启动器 Preferences → Projects Directory 设成 $(Split-Path $repo -Parent)（只需一次）"
        Write-Host "  2. 项目列表里选 $(Split-Path $repo -Leaf) → Build Distributions → 勾 Windows → Build"
        Write-Host "  3. 产物在 $(Join-Path $repo 'dist')"
        Write-Host "注意：本项目还没有实际构建成功过，产物也没在没装 SDK 的机器上试过。" -ForegroundColor Yellow

        if (Test-Path $launcher) {
            Start-Process -FilePath $launcher -WorkingDirectory $sdk
        }
        else {
            Write-Host "找不到 $launcher，请手动打开 SDK 启动器。" -ForegroundColor Red
            exit 1
        }
        exit 0
    }
    default {
        ## diversity：差异观测，不进默认链（跟 shots 一样）。
        ## 它只是 test 的一个具名用例，打印真实细节覆盖与 Jaccard，真数据缺位时判红。
        if ($Command -eq 'diversity') {
            $Command = 'test'
            if (-not $Name) { $Name = 'diversity_report' }
            ## 只有走这条命令时才判红：默认链会跑所有 case，
            ## 差异报告挂在里面会让每次提交都红，而它依赖的是还没落地的文案数据。
            $env:AIGAL_DIVERSITY = '1'
        }

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

}
finally { Exit-RenpyLock $lock }

exit $LASTEXITCODE