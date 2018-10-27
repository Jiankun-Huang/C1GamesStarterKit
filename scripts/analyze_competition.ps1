$allUsers = @{}
$pageNum = 1
$stop = 0
while($stop -ne 1) {
#while(0) {
    $request = Invoke-WebRequest -Uri https://terminal.c1games.com/api/game/leaderboard?page=$($pageNum)
    if ($request.StatusCode -eq 200) {
        (ConvertFrom-Json $request.Content).algos | ForEach-Object -Process {
            if (!$allUsers.Contains($_.user)) {
                $allUsers.Add($_.user, $_.elo)
            }
        }
    } else {
        $stop = 1
    }
    $pageNum++
    if ($pageNum -gt 98) {
        $stop = 1
    }
}

$topUsers = @()
((Invoke-WebRequest -Uri https://terminal.c1games.com/api/game/leaderboard?page=1).Content | ConvertFrom-Json).algos | ForEach-Object -Process {
    $topUsers += $_.user
    
}

((Invoke-WebRequest -Uri https://terminal.c1games.com/api/game/leaderboard?page=2).Content | ConvertFrom-Json).algos | ForEach-Object -Process {
    $topUsers += $_.user
  }

$((Invoke-WebRequest -Uri https://terminal.c1games.com/api/game/competition/27/matches).Content | ConvertFrom-Json).matches | ForEach-Object -Process {
    if ($_.round -gt 6) {
        if ($topUsers.Contains($_.winning_algo.user)) {
            Write-Output ("Round {7} Top20 win: {6} - {0}(Highest elo: {1})'s algo '{2}' beat {3}(Highest elo:{4})'s algo '{5}' in {9} turns - https://terminal.c1games.com/watch/{8}"`
                -f $_.winning_algo.user, $allUsers[$_.winning_algo.user], $_.winning_algo.name,`
                $_.losing_algo.user, $allUsers[$_.losing_algo.user], $_.losing_algo.name,`
                $_.winning_algo.user, $_.round, $_.id, $_.turns)
        }
        elseif ($topUsers.Contains($_.losing_algo.user)) {
            Write-Output ("Round {7} Top20 loss: {6} - {0}(Highest elo: {1})'s algo '{2}' beat {3}(Highest elo:{4})'s algo '{5}' in {9} turns - https://terminal.c1games.com/watch/{8}"`
                -f $_.winning_algo.user, $allUsers[$_.winning_algo.user], $_.winning_algo.name,`
                $_.losing_algo.user, $allUsers[$_.losing_algo.user], $_.losing_algo.name,`
                $_.losing_algo.user, $_.round, $_.id, $_.turns)
        }
        else {
            Write-Output ("Round {6} Match - {0}(Highest elo: {1})'s algo '{2}' beat {3}(Highest elo:{4})'s algo '{5}' in {8} turns - https://terminal.c1games.com/watch/{7}"`
                -f $_.winning_algo.user, $allUsers[$_.winning_algo.user], $_.winning_algo.name,`
                $_.losing_algo.user, $allUsers[$_.losing_algo.user], $_.losing_algo.name,`
                $_.round, $_.id, $_.turns)
        }
    }
}



