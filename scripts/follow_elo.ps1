$myAlgos = @(28459)

$myAlgos | ForEach-Object -Process {
    Write-Host ""
    Write-Host ("---" + $_ + "---") -f Blue
    $wins = 0
    $losses = 0
    $name = ""
(((Invoke-WebRequest -Uri https://terminal.c1games.com/api/game/algo/$_/matches).Content | ConvertFrom-Json).matches | ForEach-Object -Process {
    if ($_.winning_algo.user -ne "n-sanders") {
        Write-Host ("{0} lost to {1} (elo:{2}), elo is now {3}" -f $_.losing_algo.name, $_.winning_algo.name, $_.winning_algo.elo, $_.losing_algo.elo) -f Red
        $losses++
        $name = $_.losing_algo.name
    }
    else {
        Write-Host ("{0} beat {1} (elo:{2}), elo is now {3}" -f $_.winning_algo.name, $_.losing_algo.name, $_.losing_algo.elo, $_.winning_algo.elo) -f Green
        $wins++
        $name = $_.winning_algo.name
    }
})
    Write-Host ("{0} had {1} wins and {2} losses" -f $name, $wins, $losses) -f Blue
}