$cbEntries = @()
((Invoke-WebRequest -Uri https://terminal.c1games.com/api/game/competition/27/participant).Content | ConvertFrom-Json).participants | ForEach-Object -Process {
    if ($_.algo -and $_.algo.user -ne "n-sanders")
    {
        $cbEntries += $_.algo.name
    }
}


$topUsers = @()
((Invoke-WebRequest -Uri https://terminal.c1games.com/api/game/leaderboard?page=1).Content | ConvertFrom-Json).algos | ForEach-Object -Process {
    if ($_.user -ne "n-sanders")
    {
        $topUsers += $_.user
    }
}

((Invoke-WebRequest -Uri https://terminal.c1games.com/api/game/leaderboard?page=2).Content | ConvertFrom-Json).algos | ForEach-Object -Process {
    if ($_.user -ne "n-sanders")
    {
        $topUsers += $_.user
    }
  }

$myAlgos = @(24013, 26378, 26376, 26377, 26576, 26588)
$myAlgos | ForEach-Object -Process {
    Write-Host ""
    Write-Host ("---" + $_ + "---") -f Blue
    $wins = 0
    $losses = 0
    $name = ""
(((Invoke-WebRequest -Uri https://terminal.c1games.com/api/game/algo/$_/matches).Content | ConvertFrom-Json).matches | ForEach-Object -Process {
    
    if ($cbEntries.Contains(($_.losing_algo).name)) {
        Write-Host ($_.winning_algo.name + " Had a CB Entry win.  It beat " + $_.losing_algo.user + "'s " + $_.losing_algo.elo + " elo algo " + $_.losing_algo.name + " " + ([Math]::Floor((New-TimeSpan -Start ($_.date | Get-Date) -End (Get-Date)).TotalHours)) + " hours ago") -f Green
    }

    if ($topUsers.Contains(($_.losing_algo).user)) {
        Write-Host ($_.winning_algo.name + " Had a top20 player win.  It beat " + $_.losing_algo.user + "'s " + $_.losing_algo.elo + " elo algo " + $_.losing_algo.name + " " + ([Math]::Floor((New-TimeSpan -Start ($_.date | Get-Date) -End (Get-Date)).TotalHours)) + " hours ago") -f Yellow
    }

    if ($_.winning_algo.user -ne "n-sanders") {
        Write-Host ($_.losing_algo.name + " lost to " + $_.winning_algo.user + "'s " + $_.winning_algo.elo + " elo algo " + $_.winning_algo.name + " " + ([Math]::Floor((New-TimeSpan -Start ($_.date | Get-Date) -End (Get-Date)).TotalHours)) + " hours ago") -f Red
        $losses++
        $name = $_.losing_algo.name
    }
    else {
        $wins++
        $name = $_.winning_algo.name
    }
})
    Write-Host ("{0} had {1} wins and {2} losses" -f $name, $wins, $losses) -f Blue
}

