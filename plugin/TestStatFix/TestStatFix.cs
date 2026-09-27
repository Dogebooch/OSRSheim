// Client-only fix for a vanilla bug in console `test` mode (Terminal.m_showTests).
// PlayerProfile.IncrementStatBuildPiecePlaced and IncrementStatFoodEaten end with a
// test-only log line that reads m_pickableStats[name] (wrong dictionary). The
// KeyNotFoundException aborts Player.TryPlacePiece before PlacePiece (silent build
// failure) and Player.ConsumeItem before RemoveOneItem (food buff, food kept).
// The stat is already counted when the line throws, so the finalizer drops only that
// exception and logs the line with the right name. No gameplay change; no version check.
using System;
using System.Collections.Generic;
using System.Reflection;
using BepInEx;
using HarmonyLib;

namespace OSRSheim.TestStatFix
{
    [BepInPlugin("osrsheim.teststatfix", "OSRSheim Test Stat Fix", "1.0.0")]
    public class Plugin : BaseUnityPlugin
    {
        private void Awake() => new Harmony("osrsheim.teststatfix").PatchAll();
    }

    [HarmonyPatch]
    internal static class WrongDictionaryLog
    {
        private static IEnumerable<MethodBase> TargetMethods()
        {
            yield return AccessTools.Method(typeof(PlayerProfile), nameof(PlayerProfile.IncrementStatBuildPiecePlaced));
            yield return AccessTools.Method(typeof(PlayerProfile), nameof(PlayerProfile.IncrementStatFoodEaten));
        }

        private static Exception Finalizer(Exception __exception, MethodBase __originalMethod, string name, float amount)
        {
            if (!(__exception is KeyNotFoundException) || !Terminal.m_showTests)
                return __exception;
            string what = __originalMethod.Name == nameof(PlayerProfile.IncrementStatFoodEaten) ? "food eaten" : "piece placed";
            ZLog.Log($"Playerstat {what} '{name}' by {amount}");
            return null;
        }
    }
}
